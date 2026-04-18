"use client"

import React from "react"
import { AlertTriangle } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { JDEvaluationPanel } from '@/components/wsi'
import { CompanyBankQuestions } from './CompanyBankQuestions'
import { CompanyDefaultQuestions } from './CompanyDefaultQuestions'
import { CustomQuestions } from './CustomQuestions'
import type { ScreeningQuestionItem } from './SCMScreeningTypes'
import { WSI_BLOCKS, WSI_AUTOMATIC_MESSAGES, formatMessageWithVariables } from '@/constants/wsi-blocks'
import { normalizeTechnicalRequirement } from '@/lib/wsi/normalize-technical-requirement'
import { toast } from 'sonner'
import { useScreeningConfigManagerCore } from "./hooks/useScreeningConfigManagerCore"
import { SCMSectionConfiguracoes } from './SCMSectionConfiguracoes'
import { SCMSectionPerguntasEdit } from './SCMSectionPerguntasEdit'

type SCMSectionContentProps = ReturnType<typeof useScreeningConfigManagerCore>

interface JobFields {
  title: string
  requirements: string[]
  technicalRequirements: Array<Record<string, unknown>>
  behavioralCompetencies: Array<Record<string, unknown>>
  level: string
  seniority: string
  department: string
  description: string
  screeningQuestions: ScreeningQuestionItem[]
  enrichedJd: unknown
  benefits: string[]
  liaMetrics: { triagens_realizadas?: number }
  backendId: string | number
  jobId: string | number
  id: string | number
  companyId: string
  companyName: string
  industry: string
  interviewStages: Array<Record<string, unknown>>
  disabled_eligibility_question_ids: string[]
}

type TypedJob = Record<string, unknown> & Partial<JobFields>

export function SCMSectionContent(props: SCMSectionContentProps) {
  const { activeSection, isEditingScreening, job: rawJob, onJobUpdate,
    companyQuestions, disabledCompanyQIds, selectedBankQuestions, bankQuestionOverrides,
    customQuestions, handleToggleBankQuestion, handleToggleCompanyDefault,
    generatedQuestions, acceptedQuestions, setActiveSection,
  } = props
  const job = rawJob as TypedJob

  return (
    <>
      {activeSection === 'configuracoes' && (
        <SCMSectionConfiguracoes {...props} />
      )}

      {activeSection === 'descricao' && (
        <div>
          <div className="flex-1 min-w-0">
            <JDEvaluationPanel
              className="!mx-0 !mt-0"
              jobTitle={job.title as string}
              responsibilities={(job.requirements as string[]) || []}
              technicalSkills={
                ((job.technicalRequirements || []) as unknown[])
                  .map((r) => normalizeTechnicalRequirement(r))
                  .filter((s): s is string => Boolean(s))
              }
              behavioralCompetencies={(job.behavioralCompetencies || []).map((c: Record<string, unknown>) => c.competency || c.name || (typeof c === 'string' ? c : '')).filter(Boolean) as string[]}
              seniority={(job.seniority || job.level) as string | undefined}
              department={job.department as string | undefined}
              description={job.description as string | undefined}
              hasQuestions={((job.screeningQuestions as unknown[])?.length || 0) > 0}
              onGenerateQuestions={async () => {
                setActiveSection('perguntas')
                toast.success('Acesse "Perguntas de Triagem" para gerar as perguntas WSI e escolher o modo (Compacto ou Completo).')
              }}
              enrichedJd={job.enrichedJd as Record<string, unknown> | undefined}
              onSaveEnrichedJD={async (enrichedData) => {
                if (!job) return
                const jobId = job.backendId || job.jobId || String(job.id)
                await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enriched_jd: enrichedData }) })
                onJobUpdate?.({ ...job, enrichedJd: enrichedData })
              }}
              onUpdateOfficialJD={async (updates) => {
                if (!job) return
                const jobId = job.backendId || job.jobId || String(job.id)
                await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ description: updates.description, requirements: updates.requirements, technical_requirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })), behavioral_competencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) }) })
                onJobUpdate?.({ ...job, description: updates.description || job.description, requirements: updates.requirements || job.requirements, technicalRequirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })) || job.technicalRequirements, behavioralCompetencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) || job.behavioralCompetencies })
              }}
              onSaveJDInline={async (updates) => {
                if (!job) return
                const jobId = job.backendId || job.jobId || String(job.id)
                await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ description: updates.description, requirements: updates.requirements, technical_requirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })), behavioral_competencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) }) })
                onJobUpdate?.({ ...job, description: updates.description || job.description, requirements: updates.requirements || job.requirements, technicalRequirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })) || job.technicalRequirements, behavioralCompetencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) || job.behavioralCompetencies })
              }}
              isGenerating={props.isGeneratingWSI}
              companyId={(job as Record<string, unknown>).companyId as string || ''}
              companyName={(job as Record<string, unknown>).companyName as string || undefined}
              companyDescription={(job as Record<string, unknown>).companyDescription as string | undefined}
              companyIndustry={(job as Record<string, unknown>).industry as string || undefined}
              benefits={(job.benefits as string[]) || []}
              interviewStages={((job as Record<string, unknown>).interviewStages as Array<Record<string, unknown>> || []).map((s: Record<string, unknown>) => typeof s === 'string' ? s : (s.stageName || s.name || '') as string)}
              onUpdateJobDescription={async (jdText) => {
                if (!job) return
                const jobId = job.backendId || job.jobId || String(job.id)
                await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ description: jdText }) })
                onJobUpdate?.({ ...job, description: jdText })
              }}
            />
          </div>
        </div>
      )}

      {activeSection === 'perguntas' && (
        <Card className="border border-lia-border-subtle">
          {!isEditingScreening && (
            <CardContent className="p-4">
              <div className="space-y-4">
                <div>
                  <h4 className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wider mb-3">Blocos WSI</h4>
                  <div className="flex items-center gap-3 text-micro text-lia-text-secondary flex-wrap mb-3">
                    <span>Total: {(job.screeningQuestions as unknown[] | undefined)?.length || 0} perguntas WSI</span>
                    <span>•</span>
                    <span>{((job.screeningQuestions as ScreeningQuestionItem[]) || []).filter((q: ScreeningQuestionItem) => q.type === 'eliminatory' || q.required).length} eliminatórias</span>
                    <span>•</span>
                    <span>{((job.screeningQuestions as ScreeningQuestionItem[]) || []).filter((q: ScreeningQuestionItem) => q.type !== 'eliminatory' && !q.required).length} informativas</span>
                  </div>
                </div>
                <div className="space-y-2">
                  {WSI_BLOCKS.map((block) => {
                    const blockQuestions = ((job.screeningQuestions as ScreeningQuestionItem[]) || []).filter((q: ScreeningQuestionItem) => q.block_id === block.id)
                    const isAutomatic = !block.editable
                    const block2Count = block.id === 2 ? (companyQuestions.length - disabledCompanyQIds.size) + selectedBankQuestions.length + customQuestions.length : 0
                    const totalBlockCount = block.id === 2 ? block2Count + blockQuestions.length : blockQuestions.length
                    return (
                      <div key={block.id} className={`px-3 py-2 rounded-md ${isAutomatic ? 'bg-lia-bg-secondary/50 border border-lia-border-subtle' : totalBlockCount > 0 ? 'bg-lia-bg-primary border border-lia-border-subtle' : 'bg-lia-bg-primary border border-lia-border-subtle border-dashed/50'}`}>
                        <div className="flex items-center gap-2">
                          <span className={`text-micro font-semibold rounded-full w-5 h-5 flex items-center justify-center shrink-0 ${isAutomatic ? 'bg-lia-bg-tertiary' : 'text-lia-text-disabled'}`}>{block.id}</span>
                          <span className={`text-xs font-medium ${isAutomatic ? 'text-lia-text-tertiary' : 'text-lia-text-primary'}`}>{block.name}</span>
                          {isAutomatic ? (
                            <span className="text-micro px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary rounded-full font-medium uppercase tracking-wide">Automático</span>
                          ) : totalBlockCount > 0 ? (
                            <span className="text-micro text-lia-text-tertiary">({totalBlockCount} {totalBlockCount === 1 ? 'pergunta' : 'perguntas'})</span>
                          ) : (
                            <span className="text-micro text-lia-text-disabled italic">Nenhuma pergunta</span>
                          )}
                        </div>
                        {block.id === 2 && (
                          <div className="mt-2 ml-7 space-y-3">
                            {companyQuestions.length > 0 && <CompanyDefaultQuestions questions={companyQuestions} disabledIds={disabledCompanyQIds} isEditing={false} onToggle={handleToggleCompanyDefault} />}
                            {selectedBankQuestions.length > 0 && (<><div className="border-t border-lia-border-subtle" /><CompanyBankQuestions isEditing={false} selectedQuestions={selectedBankQuestions} questionOverrides={bankQuestionOverrides} onToggleQuestion={handleToggleBankQuestion} /></>)}
                            {customQuestions.length > 0 && (<><div className="border-t border-lia-border-subtle" /><CustomQuestions isEditing={false} questions={customQuestions} onAddQuestion={props.handleAddCustomQuestion} onRemoveQuestion={props.handleRemoveCustomQuestion} onUpdateQuestion={props.handleUpdateCustomQuestion} /></>)}
                          </div>
                        )}
                        {!isAutomatic && block.id !== 2 && blockQuestions.length > 0 && (
                          <div className="space-y-1 ml-7 mt-1.5">
                            {blockQuestions.map((q: ScreeningQuestionItem, idx: number) => (
                              <p key={q.id || idx} className="text-xs text-lia-text-secondary leading-relaxed truncate">• {q.question || q.text}</p>
                            ))}
                          </div>
                        )}
                        {isAutomatic && WSI_AUTOMATIC_MESSAGES[block.id] && (
                          <div className="ml-7 mt-1.5">
                            <p className="text-micro font-medium text-lia-text-tertiary mb-1">{WSI_AUTOMATIC_MESSAGES[block.id].title}</p>
                            <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-lg px-2.5 py-2">
                              <p className="text-micro text-lia-text-secondary leading-relaxed whitespace-pre-line">{formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}</p>
                            </div>
                            <p className="text-micro text-lia-text-disabled mt-1 italic">{WSI_AUTOMATIC_MESSAGES[block.id].note}</p>
                          </div>
                        )}
                        {isAutomatic && !WSI_AUTOMATIC_MESSAGES[block.id] && (
                          <p className="text-micro text-lia-text-disabled ml-7 mt-0.5">{block.description}</p>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            </CardContent>
          )}

          {isEditingScreening && (
            <SCMSectionPerguntasEdit {...props} />
          )}
        </Card>
      )}

      {((job.liaMetrics as { triagens_realizadas?: number } | undefined)?.triagens_realizadas ?? 0) > 0 && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-status-warning/10 border border-status-warning/30 rounded-xl dark:bg-status-warning/10 dark:border-status-warning/30">
          <AlertTriangle className="w-3.5 h-3.5 text-status-warning shrink-0" />
          <p className="text-xs text-status-warning">
            <span className="font-bold">Triagem em andamento</span> — <span className="font-semibold" aria-live="polite" aria-atomic="true">{(job.liaMetrics as { triagens_realizadas?: number } | undefined)?.triagens_realizadas} candidatos</span> já triados. Alterar perguntas pode afetar a comparabilidade entre candidatos.
          </p>
        </div>
      )}
    </>
  )
}
