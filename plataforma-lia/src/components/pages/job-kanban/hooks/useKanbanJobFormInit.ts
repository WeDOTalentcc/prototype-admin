"use client"

import { useState, useEffect } from "react"
import { useCompanyDefaults } from "@/hooks/company/use-company-defaults"
import { getCompanyPipelineStages } from "@/lib/recruitment-stages"

export function useKanbanJobFormInit(currentJob: Record<string, unknown> | null) {
  const [jobEditForm, setJobEditForm] = useState<Record<string, unknown>>({})
  const { defaults: companyDefaults } = useCompanyDefaults()

  useEffect(() => {
    if (!currentJob) return
    setJobEditForm({
      title: currentJob.title || '',
      department: currentJob.department || '',
      location: currentJob.location || '',
      workModel: currentJob.workModel || '',
      type: currentJob.type || '',
      level: currentJob.level || '',
      status: currentJob.status || '',
      urgencyLevel: currentJob.urgencyLevel || 3,
      recruiter: currentJob.recruiter || '',
      recruiterEmail: currentJob.recruiterEmail || '',
      manager: currentJob.manager || currentJob.hiringManager || '',
      managerEmail: currentJob.managerEmail || currentJob.hiringManagerEmail || '',
      openDate: currentJob.openDate || '',
      deadline: currentJob.deadline || '',
      deadlineScreening: currentJob.deadlineScreening || '',
      deadlineShortlist: currentJob.deadlineShortlist || '',
      deadlineClosing: currentJob.deadlineClosing || '',
      salaryMin: (currentJob.salaryRange as Record<string,unknown>|undefined)?.min || currentJob.salaryMin || '',
      salaryMax: (currentJob.salaryRange as Record<string,unknown>|undefined)?.max || currentJob.salaryMax || '',
      salaryUndisclosed: (currentJob.salaryRange as Record<string,unknown>|undefined)?.undisclosed || (currentJob as Record<string,unknown>).salaryUndisclosed || false,
      bonusMin: (currentJob.bonusRange as Record<string,unknown>|undefined)?.min || (currentJob.bonus_range as Record<string,unknown>|undefined)?.min || '',
      bonusMax: (currentJob.bonusRange as Record<string,unknown>|undefined)?.max || (currentJob.bonus_range as Record<string,unknown>|undefined)?.max || '',
      benefits: currentJob.benefits || [],
      variable_compensation: (currentJob as Record<string, unknown>).variable_compensation || [],
      targetAudience: currentJob.targetAudience || '',
      targetSector: currentJob.targetSector || '',
      targetSegment: currentJob.targetSegment || '',
      languages: currentJob.languages || [],
      visibility: currentJob.visibility || 'internal',
      isConfidential: currentJob.isConfidential || false,
      maskedCompanyName: currentJob.maskedCompanyName || '',
      isAffirmative: currentJob.isAffirmative || false,
      affirmativeCriteriaPrimary: currentJob.affirmativeCriteriaPrimary || currentJob.affirmativeType || '',
      affirmativeCriteriaSecondary: currentJob.affirmativeCriteriaSecondary || '',
      affirmativeDescription: currentJob.affirmativeDescription || '',
      affirmativeDocumentRequired: currentJob.affirmativeDocumentRequired || false,
      affirmativeDocumentTypes: currentJob.affirmativeDocumentTypes || [],
      priority: currentJob.priority || 'média',
      description: currentJob.description || '',
      interviewStages: ((currentJob.interviewStages as unknown[]) && (currentJob.interviewStages as unknown[]).length > 0 && (currentJob.interviewStages as Record<string, unknown>[])[0]?.stageCategory)
        ? currentJob.interviewStages
        : (() => {
            const pipeline = getCompanyPipelineStages()
            return pipeline
              .filter(s => s.isActive)
              .map((s, i) => ({
                stageName: s.displayName,
                order: i + 1,
                type: 'interview' as const,
                name: s.name,
                stageCategory: s.stageCategory,
                isEditable: s.isEditable,
                isRemovable: s.isRemovable,
                isReorderable: s.isReorderable,
                isInitial: s.isInitial,
                isFinal: s.isFinal,
                isHired: s.isHired,
                isRejection: s.isRejection,
                color: s.color,
                stageType: s.stageType,
                slaDays: s.defaultSlaDays,
                defaultSlaDays: s.defaultSlaDays,
                liaAssisted: s.liaAssisted,
              }))
          })(),
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: only re-initialize form when job ID changes, not on every field change
  }, [currentJob?.id])

  useEffect(() => {
    if (!companyDefaults?.defaultLanguages?.length) return
    if (jobEditForm.languages && (jobEditForm.languages as unknown[]).length > 0) return

    const prefilled = companyDefaults.defaultLanguages.map((lang: string) => ({
      language: lang,
      level: 'Intermediário',
      required: false,
    }))
    setJobEditForm(prev => ({ ...prev, languages: prefilled }))
  }, [companyDefaults?.defaultLanguages, jobEditForm.languages])

  return { jobEditForm, setJobEditForm, companyDefaults }
}
