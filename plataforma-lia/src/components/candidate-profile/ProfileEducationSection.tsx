"use client"

import { GraduationCap } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface EducationEntry {
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
        <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
          <GraduationCap className="w-4 h-4 lia-text-600" />
          Formação Acadêmica
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-4 space-y-3">
        {education.length > 0 ? (
          education.map((edu, index) => (
            <div
              key={}
              className={}
            >
              <div>
                <h5 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                  {edu.degree || edu.title || "Formação"}
                  {(edu.field_of_study || edu.fieldOfStudy) &&
                    }
                </h5>
                <p className="text-sm lia-text-600 dark:text-lia-text-tertiary">
                  {edu.school || edu.institution || "Instituição não informada"}
                </p>
              </div>
              <span className="text-xs lia-text-500 whitespace-nowrap">
                {edu.start_date || edu.startDate || ""}
                {(edu.start_date || edu.startDate) && (edu.end_date || edu.endDate) ? " - " : ""}
                {edu.end_date || edu.endDate || ""}
              </span>
            </div>
          ))
        ) : (
          <p className="text-sm lia-text-500 italic">Não informado</p>
        )}
      </CardContent>
    </Card>
  )
}
