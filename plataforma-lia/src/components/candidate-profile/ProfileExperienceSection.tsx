"use client"

import { Building2, Code, Users, Briefcase } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface ExperienceEntry {
  title?: string
  position?: string
  role?: string
  company?: string
  company_name?: string
  location?: string
  start_date?: string
  startDate?: string
  end_date?: string
  endDate?: string
  is_current?: boolean
  description?: string
  industries?: string[]
  technologies?: string[]
  company_size?: string
  company_size_range?: string
  is_startup?: boolean
  duration_years?: number
  [key: string]: unknown
}

interface ProfileExperienceSectionProps {
  experiences: ExperienceEntry[]
  formatDateShort: (date: string | null | undefined) => string
}

export function ProfileExperienceSection({ experiences, formatDateShort }: ProfileExperienceSectionProps) {
  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-2.5 px-4">
        <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
          <Briefcase className="w-4 h-4 lia-text-600" />
          Experiência Profissional
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-4 space-y-4">
        {experiences.length > 0 ? (
          experiences.map((exp, index) => {
            const title = exp.title || exp.position || exp.role || ""
            const company = exp.company || exp.company_name || ""
            const location = exp.location || ""
            const startDate = exp.start_date || exp.startDate || ""
            const endDate = exp.is_current ? "Atual" : (exp.end_date || exp.endDate || "")
            const description = exp.description || ""
            const industries = Array.isArray(exp.industries) ? exp.industries : []
            const technologies = Array.isArray(exp.technologies) ? exp.technologies : []
            const companySize = exp.company_size || exp.company_size_range || null
            const isStartup = exp.is_startup

            return (
              <div
                key={}
                className={}
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div>
                    <h5 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                      {title || "Cargo não informado"}
                    </h5>
                    <p className="text-sm lia-text-600 dark:text-lia-text-tertiary">
                      {company || "Empresa não informada"}
                      {location && }
                      {exp.duration_years != null && (
                        <span className="lia-text-400 ml-1">({exp.duration_years.toFixed(1)} anos)</span>
                      )}
                    </p>
                  </div>
                  <span className="text-xs lia-text-500 whitespace-nowrap">
                    {formatDateShort(startDate)}
                    {startDate && endDate ? " - " : ""}
                    {endDate === "Atual" ? "Atual" : formatDateShort(endDate)}
                  </span>
                </div>

                <div className="flex flex-wrap gap-1.5 mb-2">
                  {industries.slice(0, 2).map((ind: string) => (
                    <span
                      key={ind}
                      className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro bg-gray-50 dark:bg-lia-bg-secondary lia-text-900 dark:text-lia-text-secondary border border-lia-border-subtle"
                    >
                      <Building2 className="w-2.5 h-2.5 mr-0.5" />
                      {ind}
                    </span>
                  ))}
                  {isStartup && (
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-status-success/10 text-status-success border border-status-success/30">
                      🚀 Startup
                    </span>
                  )}
                  {companySize && (
                    <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-micro bg-gray-50 dark:bg-lia-bg-secondary lia-text-600 dark:text-lia-text-tertiary border border-lia-border-subtle">
                      <Users className="w-2.5 h-2.5" />
                      {companySize}
                    </span>
                  )}
                </div>

                {technologies.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    <span className="text-micro lia-text-400 flex items-center gap-0.5">
                      <Code className="w-2.5 h-2.5" />
                      Stack:
                    </span>
                    {technologies.slice(0, 6).map((tech: string) => (
                      <span
                        key={tech}
                        className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-gray-100 dark:bg-lia-bg-secondary lia-text-800 dark:text-lia-text-primary"
                      >
                        {tech}
                      </span>
                    ))}
                    {technologies.length > 6 && (
                      <span className="text-micro lia-text-400">+{technologies.length - 6}</span>
                    )}
                  </div>
                )}

                {description && (
                  <p className="text-xs lia-text-600 dark:text-lia-text-tertiary mt-1">{description}</p>
                )}
              </div>
            )
          })
        ) : (
          <p className="text-sm lia-text-500 italic">Não informado</p>
        )}
      </CardContent>
    </Card>
  )
}
