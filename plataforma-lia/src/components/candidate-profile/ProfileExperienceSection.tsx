"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { Building2, Code, Users, Briefcase, Pencil, Plus } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useCandidateEdit } from "./CandidateEditContext"
import { useCandidateArrayUpdate } from "@/hooks/candidates/use-candidate-array-update"
import { EditArrayItemModal, type FieldDef } from "./EditArrayItemModal"

export interface ExperienceEntry {
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

const EXPERIENCE_FIELDS: FieldDef[] = [
  { name: "title", label: "Cargo / Posição", required: true, placeholder: "Tech Lead" },
  { name: "company", label: "Empresa", required: true, placeholder: "Acme Co" },
  { name: "location", label: "Localização", placeholder: "São Paulo, SP" },
  { name: "start_date", label: "Início", placeholder: "2020-01" },
  { name: "end_date", label: "Fim", placeholder: "2024-12 ou Atual" },
  { name: "description", label: "Descrição", type: "textarea", placeholder: "Principais responsabilidades..." },
]

export function ProfileExperienceSection({ experiences, formatDateShort }: ProfileExperienceSectionProps) {
  const t = useTranslations('candidates.profile')
  const { editable, candidateId } = useCandidateEdit()
  const { updateItem, addItem, saving } = useCandidateArrayUpdate<ExperienceEntry>(candidateId, "work_history", experiences)
  const [modal, setModal] = useState<{ open: boolean; item: ExperienceEntry | null; index: number | null }>({
    open: false, item: null, index: null,
  })
  const openAdd = () => setModal({ open: true, item: null, index: null })
  const openEdit = (item: ExperienceEntry, index: number) => setModal({ open: true, item, index })
  const closeModal = () => setModal({ open: false, item: null, index: null })
  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-2.5 px-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-lia-text-secondary" aria-hidden="true" />
            {t('experienceTitle')}
          </CardTitle>
          {editable && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs gap-1"
              onClick={openAdd}
              disabled={saving}
              aria-label="Adicionar experiência"
            >
              <Plus className="w-3 h-3" aria-hidden="true" />
              Adicionar
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="px-4 pb-4 space-y-4">
        {experiences.length > 0 ? (
          experiences.map((exp, index) => {
            const title = exp.title || exp.position || exp.role || ""
            const company = exp.company || exp.company_name || ""
            const location = exp.location || ""
            const startDate = exp.start_date || exp.startDate || ""
            const endDate = exp.is_current ? t('current') : (exp.end_date || exp.endDate || "")
            const description = exp.description || ""
            const industries = Array.isArray(exp.industries) ? exp.industries : []
            const technologies = Array.isArray(exp.technologies) ? exp.technologies : []
            const companySize = exp.company_size || exp.company_size_range || null
            const isStartup = exp.is_startup

            return (
              <div
                key={index}
                className="pb-3 last:border-0 last:pb-0"
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="flex-1 min-w-0">
                    <h5 className="text-sm font-medium text-lia-text-primary">
                      {title || t('positionNotProvided')}
                    </h5>
                    <p className="text-sm text-lia-text-secondary">
                      {company || t('companyNotProvided')}
                      {location && <span className="text-lia-text-tertiary"> · {location}</span>}
                      {exp.duration_years != null && (
                        <span className="text-lia-text-tertiary ml-1">({t('durationYears', { years: exp.duration_years.toFixed(1) })})</span>
                      )}
                    </p>
                  </div>
                  <span className="text-xs text-lia-text-secondary whitespace-nowrap">
                    {formatDateShort(startDate)}
                    {startDate && endDate ? " - " : ""}
                    {endDate === t('current') ? t('current') : formatDateShort(endDate)}
                  </span>
                  {editable && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={() => openEdit(exp, index)}
                      disabled={saving}
                      aria-label={`Editar experiência ${index + 1}`}
                    >
                      <Pencil className="w-3 h-3 text-lia-text-secondary" aria-hidden="true" />
                    </Button>
                  )}
                </div>

                <div className="flex flex-wrap gap-1.5 mb-2">
                  {industries.slice(0, 2).map((ind: string) => (
                    <span
                      key={ind}
                      className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro bg-lia-bg-secondary dark:bg-lia-bg-secondary text-lia-text-primary border border-lia-border-subtle"
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
                    <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-micro bg-lia-bg-secondary dark:bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle">
                      <Users className="w-2.5 h-2.5" />
                      {companySize}
                    </span>
                  )}
                </div>

                {technologies.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    <span className="text-micro text-lia-text-tertiary flex items-center gap-0.5">
                      <Code className="w-2.5 h-2.5" />
                      {t('techStack')}:
                    </span>
                    {technologies.slice(0, 6).map((tech: string) => (
                      <span
                        key={tech}
                        className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary"
                      >
                        {tech}
                      </span>
                    ))}
                    {technologies.length > 6 && (
                      <span className="text-micro text-lia-text-tertiary">+{technologies.length - 6}</span>
                    )}
                  </div>
                )}

                {description && (
                  <p className="text-xs text-lia-text-secondary mt-1">{description}</p>
                )}
              </div>
            )
          })
        ) : (
          <p className="text-sm text-lia-text-secondary italic" role="status" aria-live="polite">{t('notProvided')}</p>
        )}
      </CardContent>
      <EditArrayItemModal<ExperienceEntry>
        open={modal.open}
        onClose={closeModal}
        initialItem={modal.item}
        fields={EXPERIENCE_FIELDS}
        title={modal.index === null ? "Adicionar experiência" : "Editar experiência"}
        onSave={async (item) => {
          if (modal.index === null) return await addItem(item)
          return await updateItem(modal.index, item)
        }}
      />
    </Card>
  )
}
