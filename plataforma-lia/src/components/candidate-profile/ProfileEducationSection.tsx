"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { GraduationCap, Pencil, Plus } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useCandidateEdit } from "./CandidateEditContext"
import { useCandidateArrayUpdate } from "@/hooks/candidates/use-candidate-array-update"
import { EditArrayItemModal, type FieldDef } from "./EditArrayItemModal"

export interface EducationEntry {
  degree?: string
  title?: string
  field_of_study?: string
  fieldOfStudy?: string
  school?: string
  institution?: string
  start_date?: string
  startDate?: string
  end_date?: string
  endDate?: string
  [key: string]: unknown
}

interface ProfileEducationSectionProps {
  education: EducationEntry[]
}

const EDUCATION_FIELDS: FieldDef[] = [
  { name: "degree", label: "Título / Grau", required: true, placeholder: "Bacharelado" },
  { name: "field_of_study", label: "Área", placeholder: "Engenharia da Computação" },
  { name: "institution", label: "Instituição", required: true, placeholder: "USP" },
  { name: "start_date", label: "Início", placeholder: "2010" },
  { name: "end_date", label: "Fim", placeholder: "2014" },
]

export function ProfileEducationSection({ education }: ProfileEducationSectionProps) {
  const t = useTranslations('candidates.profile')
  const { editable, candidateId } = useCandidateEdit()
  const { updateItem, addItem, saving } = useCandidateArrayUpdate<EducationEntry>(candidateId, "education", education)
  const [modal, setModal] = useState<{ open: boolean; item: EducationEntry | null; index: number | null }>({
    open: false, item: null, index: null,
  })
  const openAdd = () => setModal({ open: true, item: null, index: null })
  const openEdit = (item: EducationEntry, index: number) => setModal({ open: true, item, index })
  const closeModal = () => setModal({ open: false, item: null, index: null })
  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-2.5 px-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
            <GraduationCap className="w-4 h-4 text-lia-text-secondary" aria-hidden="true" />
            {t('educationTitle')}
          </CardTitle>
          {editable && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs gap-1"
              onClick={openAdd}
              disabled={saving}
              aria-label="Adicionar formação"
            >
              <Plus className="w-3 h-3" aria-hidden="true" />
              Adicionar
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="px-4 pb-4 space-y-3">
        {education.length > 0 ? (
          education.map((edu, index) => (
            <div
              key={index}
              className="flex items-start justify-between gap-2"
            >
              <div className="flex-1 min-w-0">
                <h5 className="text-sm font-medium text-lia-text-primary">
                  {edu.degree || edu.title || t('educationDegreeDefault')}
                  {(edu.field_of_study || edu.fieldOfStudy) &&
                    ` ${t('educationFieldIn')} ${edu.field_of_study || edu.fieldOfStudy}`}
                </h5>
                <p className="text-sm text-lia-text-secondary">
                  {edu.school || edu.institution || t('institutionNotProvided')}
                </p>
              </div>
              <span className="text-xs text-lia-text-secondary whitespace-nowrap">
                {edu.start_date || edu.startDate || ""}
                {(edu.start_date || edu.startDate) && (edu.end_date || edu.endDate) ? " - " : ""}
                {edu.end_date || edu.endDate || ""}
              </span>
              {editable && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={() => openEdit(edu, index)}
                  disabled={saving}
                  aria-label={`Editar formação ${index + 1}`}
                >
                  <Pencil className="w-3 h-3 text-lia-text-secondary" aria-hidden="true" />
                </Button>
              )}
            </div>
          ))
        ) : (
          <p className="text-sm text-lia-text-secondary italic" role="status" aria-live="polite">{t('notProvided')}</p>
        )}
      </CardContent>
      <EditArrayItemModal<EducationEntry>
        open={modal.open}
        onClose={closeModal}
        initialItem={modal.item}
        fields={EDUCATION_FIELDS}
        title={modal.index === null ? "Adicionar formação" : "Editar formação"}
        onSave={async (item) => {
          if (modal.index === null) return await addItem(item)
          return await updateItem(modal.index, item)
        }}
      />
    </Card>
  )
}
