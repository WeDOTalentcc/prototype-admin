"use client"

import React from "react"
import {
  Users,
  CheckCircle,
  Clock,
  DollarSign,
  MapPin,
  Brain,
  Target,
  Award,
  Gift,
  Briefcase,
} from "lucide-react"
import type { ComparisonDimension, JobCompareItem } from "./useJobCompare"

interface JobCompareTableProps {
  jobs: JobCompareItem[]
  selectedDimensions: Set<ComparisonDimension>
  formatSalaryRange: (range?: { min?: number; max?: number }) => string
  getScoreColor: (score?: number) => string
}

export function JobCompareTable({
  jobs,
  selectedDimensions,
  formatSalaryRange,
  getScoreColor,
}: JobCompareTableProps) {
  return (
    <div data-testid="job-compare-table" className="overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="bg-lia-bg-secondary">
            <th className="text-left font-semibold text-lia-text-secondary uppercase tracking-wide p-2.5 border border-lia-border-subtle w-[100px]">
              Métrica
            </th>
            {jobs.map((job) => (
              <th
                key={job.id}
                className="text-left font-semibold text-lia-text-primary p-2.5 border border-lia-border-subtle min-w-[180px]"
              >
                <div className="flex flex-col gap-0.5">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {job.code && (
                      <span className="text-micro text-lia-text-secondary bg-lia-bg-tertiary px-1.5 py-0.5 rounded-full font-medium">
                        {job.code}
                      </span>
                    )}
                    <span className="text-lia-text-primary text-xs font-semibold">
                      {job.title}
                    </span>
                  </div>
                  {job.department && (
                    <span className="text-micro font-normal text-lia-text-tertiary">{job.department}</span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr className="hover:bg-lia-interactive-hover">
            <td className="text-lia-text-primary p-2.5 border border-lia-border-subtle">
              <div className="flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-lia-text-tertiary" />
                Candidatos
              </div>
            </td>
            {jobs.map((job) => (
              <td key={job.id} className="text-lia-text-primary p-2.5 border border-lia-border-subtle font-medium text-base-ui">
                {job.candidates_count ?? "-"}
              </td>
            ))}
          </tr>

          <tr className="hover:bg-lia-interactive-hover">
            <td className="text-lia-text-primary p-2.5 border border-lia-border-subtle">
              <div className="flex items-center gap-1.5">
                <CheckCircle className="w-3.5 h-3.5 text-status-success" />
                Aprovados
              </div>
            </td>
            {jobs.map((job) => (
              <td key={job.id} className="text-lia-text-secondary p-2.5 border border-lia-border-subtle font-semibold text-base-ui">
                {job.approved_count ?? "-"}
              </td>
            ))}
          </tr>

          <tr className="hover:bg-lia-interactive-hover">
            <td className="text-lia-text-primary p-2.5 border border-lia-border-subtle">
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-lia-text-secondary" />
                Triagem
              </div>
            </td>
            {jobs.map((job) => (
              <td key={job.id} className="text-lia-text-primary p-2.5 border border-lia-border-subtle font-medium text-base-ui">
                {job.screening_count ?? "-"}
              </td>
            ))}
          </tr>

          {selectedDimensions.has("salary_range") && (
            <tr className="hover:bg-lia-interactive-hover">
              <td className="text-lia-text-primary p-2.5 border border-lia-border-subtle">
                <div className="flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-lia-text-tertiary" />
                  Salário
                </div>
              </td>
              {jobs.map((job) => (
                <td key={job.id} className="text-lia-text-primary p-2.5 border border-lia-border-subtle text-xs">
                  {formatSalaryRange(job.salary_range)}
                </td>
              ))}
            </tr>
          )}

          {selectedDimensions.has("location") && (
            <tr className="hover:bg-lia-interactive-hover">
              <td className="text-lia-text-primary p-2.5 border border-lia-border-subtle">
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-lia-text-tertiary" />
                  Local
                </div>
              </td>
              {jobs.map((job) => (
                <td key={job.id} className="text-lia-text-primary p-2.5 border border-lia-border-subtle text-xs">
                  {job.location || "-"} {job.work_model && `(${job.work_model})`}
                </td>
              ))}
            </tr>
          )}

          {selectedDimensions.has("performance") && (
            <tr className="hover:bg-lia-interactive-hover bg-lia-bg-secondary">
              <td className="text-lia-text-primary p-2.5 border border-lia-border-subtle">
                <div className="flex items-center gap-1.5">
                  <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                  Performance
                </div>
              </td>
              {jobs.map((job) => (
                <td key={job.id} className="p-2.5 border border-lia-border-subtle">
                  <span className={`text-base-ui font-semibold ${getScoreColor(job.performance_score)}`}>
                    {job.performance_score ? `${job.performance_score}%` : "-"}
                  </span>
                </td>
              ))}
            </tr>
          )}

          {selectedDimensions.has("technical_requirements") && (
            <tr className="hover:bg-lia-interactive-hover">
              <td className="text-lia-text-primary p-2.5 border border-lia-border-subtle align-top">
                <div className="flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-lia-text-tertiary" />
                  Requisitos
                </div>
              </td>
              {jobs.map((job) => (
                <td key={job.id} className="text-lia-text-primary p-2.5 border border-lia-border-subtle align-top">
                  {job.technical_requirements && job.technical_requirements.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {job.technical_requirements.slice(0, 4).map((req, idx) => (
                        <span key={`req-${idx}`} className="px-1.5 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary">
                          {typeof req === "string" ? req : ((req as Record<string, unknown>).name as string || (req as Record<string, unknown>).skill as string || "-")}
                        </span>
                      ))}
                      {job.technical_requirements.length > 4 && (
                        <span className="px-1.5 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-tertiary">
                          +{job.technical_requirements.length - 4}
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-lia-text-disabled">-</span>
                  )}
                </td>
              ))}
            </tr>
          )}

          {selectedDimensions.has("competencies") && (
            <tr className="hover:bg-lia-interactive-hover">
              <td className="text-lia-text-primary p-2.5 border border-lia-border-subtle align-top">
                <div className="flex items-center gap-1.5">
                  <Award className="w-3.5 h-3.5 text-lia-text-tertiary" />
                  Competências
                </div>
              </td>
              {jobs.map((job) => (
                <td key={job.id} className="text-lia-text-primary p-2.5 border border-lia-border-subtle align-top">
                  {job.behavioral_competencies && job.behavioral_competencies.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {job.behavioral_competencies.slice(0, 4).map((comp, idx) => (
                        <span key={`comp-${idx}`} className="px-1.5 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary">
                          {typeof comp === "string" ? comp : ((comp as Record<string, unknown>).name as string || (comp as Record<string, unknown>).competency as string || "-")}
                        </span>
                      ))}
                      {job.behavioral_competencies.length > 4 && (
                        <span className="px-1.5 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-tertiary">
                          +{job.behavioral_competencies.length - 4}
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-lia-text-disabled">-</span>
                  )}
                </td>
              ))}
            </tr>
          )}

          {selectedDimensions.has("benefits") && (
            <tr className="hover:bg-lia-interactive-hover">
              <td className="text-lia-text-primary p-2.5 border border-lia-border-subtle align-top">
                <div className="flex items-center gap-1.5">
                  <Gift className="w-3.5 h-3.5 text-lia-text-tertiary" />
                  Benefícios
                </div>
              </td>
              {jobs.map((job) => (
                <td key={job.id} className="text-lia-text-primary p-2.5 border border-lia-border-subtle align-top">
                  {job.benefits && job.benefits.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {job.benefits.slice(0, 4).map((benefit, idx) => (
                        <span key={`ben-${idx}`} className="px-1.5 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary">
                          {benefit}
                        </span>
                      ))}
                      {job.benefits.length > 4 && (
                        <span className="px-1.5 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-tertiary">
                          +{job.benefits.length - 4}
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-lia-text-disabled">-</span>
                  )}
                </td>
              ))}
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
