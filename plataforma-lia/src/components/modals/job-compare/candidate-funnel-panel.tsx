"use client"

import { Filter } from "lucide-react"

const JOB_COLORS = [
  { bar: "bg-lia-btn-primary-bg", text: "text-lia-text-secondary", light: "bg-lia-bg-tertiary" },
  { bar: "bg-wedo-purple", text: "text-wedo-purple-text", light: "bg-wedo-purple/15" },
  { bar: "bg-status-success", text: "text-status-success", light: "bg-status-success/15" },
  { bar: "bg-wedo-orange", text: "text-wedo-orange-text", light: "bg-wedo-orange/15" },
]

interface Job {
  id: string
  code?: string
  title: string
  candidates_count?: number
  approved_count?: number
  screening_count?: number
}

interface CandidateFunnelPanelProps {
  jobs: Job[]
}

export function CandidateFunnelPanel({ jobs }: CandidateFunnelPanelProps) {
  return (
    <div data-testid="candidate-funnel-panel" className="border border-lia-border-subtle rounded-xl overflow-hidden">
      <div className="bg-lia-bg-secondary px-4 py-2.5">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-lia-bg-tertiary rounded-xl flex items-center justify-center">
            <Filter className="w-3.5 h-3.5 text-lia-text-secondary" />
          </div>
          <h3 className="text-base-ui font-semibold text-lia-text-primary">Funil de Candidatos</h3>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {jobs.map((job, jobIndex) => {
          const jobColor = JOB_COLORS[jobIndex % JOB_COLORS.length]
          const total = job.candidates_count || 0
          const screening = job.screening_count || 0
          const approved = job.approved_count || 0
          const screeningPct = total > 0 ? (screening / total * 100) : 0
          const approvedPct = total > 0 ? (approved / total * 100) : 0

          return (
            <div key={job.id} className="space-y-2">
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-2.5 h-2.5 rounded-full ${jobColor.bar}`} />
                <span className="text-xs font-semibold text-lia-text-primary">
                  {job.code && <span className={`${jobColor.text} mr-1.5`}>[{job.code}]</span>}
                  {job.title}
                </span>
              </div>

              <div className="space-y-1.5 pl-4">
                <div className="flex items-center gap-3">
                  <span className="text-micro text-lia-text-secondary w-[70px]">Candidatos</span>
                  <div className="flex-1 h-4 bg-lia-bg-tertiary rounded-xl overflow-hidden">
                    <div
                      className={`h-full ${jobColor.bar} transition-[width,height] duration-300`}
                     
                    />
                  </div>
                  <span className={`text-xs font-semibold w-20 text-right ${jobColor.text}`}>
                    {total} (100%)
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-micro text-lia-text-secondary w-[70px]">Em Triagem</span>
                  <div className="flex-1 h-4 bg-lia-bg-tertiary rounded-xl overflow-hidden">
                    <div
                      className={`h-full ${jobColor.bar} opacity-70 transition-[width,height] duration-300`}
                      style={{ width: `${Math.max(screeningPct, 0)}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium w-20 text-right text-lia-text-secondary">
                    {screening} ({screeningPct.toFixed(0)}%)
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-micro text-lia-text-secondary w-[70px]">Aprovados</span>
                  <div className="flex-1 h-4 bg-lia-bg-tertiary rounded-xl overflow-hidden">
                    <div
                      className={`h-full ${jobColor.bar} opacity-50 transition-[width,height] duration-300`}
                      style={{ width: `${Math.max(approvedPct, 0)}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium w-20 text-right text-lia-text-secondary">
                    {approved} ({approvedPct.toFixed(0)}%)
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
