"use client"

import { GraduationCap } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

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

export function ProfileEducationSection({ education }: ProfileEducationSectionProps) {
  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-2.5 px-4">
        <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
          <GraduationCap className="w-4 h-4 text-lia-text-secondary" />
          Formação Acadêmica
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-4 space-y-3">
        {education.length > 0 ? (
          education.map((edu, index) => (
            <div
              key={index}
              className="flex items-start justify-between gap-2"
            >
              <div>
                <h5 className="text-sm font-medium text-lia-text-primary">
                  {edu.degree || edu.title || "Formação"}
                  {(edu.field_of_study || edu.fieldOfStudy) &&
                    ` em ${edu.field_of_study || edu.fieldOfStudy}`}
                </h5>
                <p className="text-sm text-lia-text-secondary">
                  {edu.school || edu.institution || "Instituição não informada"}
                </p>
              </div>
              <span className="text-xs text-lia-text-secondary whitespace-nowrap">
                {edu.start_date || edu.startDate || ""}
                {(edu.start_date || edu.startDate) && (edu.end_date || edu.endDate) ? " - " : ""}
                {edu.end_date || edu.endDate || ""}
              </span>
            </div>
          ))
        ) : (
          <p className="text-sm text-lia-text-secondary italic">Não informado</p>
        )}
      </CardContent>
    </Card>
  )
}
