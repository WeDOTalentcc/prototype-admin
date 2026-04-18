"use client"

import React, { useMemo } from "react"
import { useTranslations, useLocale } from "next-intl"
import { ScrollArea } from "@/components/ui/scroll-area"
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
  }), [t])

  const jobById = useMemo(() => {
    const m = new Map<string, Job>()
    jobs.forEach(j => m.set(String(j.id), j))
    return m
  }, [jobs])

  return (
    <div className="flex-1 min-h-0 overflow-hidden">
      <ScrollArea className="h-full">
        <div className="flex gap-3 pb-2">
          {JOB_KANBAN_COLUMNS.map((col) => {
            const colJobs = grouped[col.id] ?? []
            const items = colJobs.map((job) => jobToKanbanItem(job, { locale, labels }))
            return (
              <KanbanColumn
                key={col.id}
                stage={{ id: col.id, name: t(`columns.${col.id}`), color: col.colorVar }}
                items={items}
                onItemClick={(item) => {
                  const job = jobById.get(item.id)
                  if (job) onJobClick(job)
                }}
                isDragDisabled
                emptyMessage={t("emptyColumn")}
              />
            )
          })}
        </div>
      </ScrollArea>
    </div>
  )
}
