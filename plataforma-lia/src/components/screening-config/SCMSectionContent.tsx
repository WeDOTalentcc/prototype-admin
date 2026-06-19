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
import { getJobSeniority } from '@/lib/jobs/seniority'
import { toast } from 'sonner'
import { useScreeningConfigManagerCore } from "./hooks/useScreeningConfigManagerCore"
import { SCMSectionConfiguracoes } from './SCMSectionConfiguracoes'
import { SCMSectionPerguntasEdit } from './SCMSectionPerguntasEdit'

type SCMSectionContentProps = ReturnType<typeof useScreeningConfigManagerCore>

interface JobFields {
  title: string
  // T-1166 — canonical field for job duties, separated from `requirements`.
  // Backend now persists it in `job_vacancies.responsibilities` (migration 132).
  responsibilities: string[]
  requirements: string[]
  technicalRequirements: Array<Record<string, unknown>>
  behavioralCompetencies: Array<Record<string, unknown>>
  /** @deprecated use `seniority` (canônico SSOT em job.schema.ts). Mantido por
   * DTOs legacy ainda em uso em ~5 arquivos do monolito. */
  level?: string
  seniority?: string
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
              // T-1166 + T-1167 — Prefer `enrichedJd.responsibilities` when present
              // (set by the JD editor's "Save Enriched" flow), otherwise fall back
              // to the persisted `job.responsibilities` column (migration 132).
              // Legacy vagas (pre-migration 132) may have BOTH null; explicit `[]`
              // is the only safe default. NEVER fall back to `job.requirements`
              // — that collapses tech skills into the "RESPONSABILIDADES" bullet
              // list (vaga 200 bug). The mescla `enrichedJd ?? job` keeps the JD
              // evaluation API in sync with what the user sees on screen, fixing
              // D2 (Responsibilities) and D9 (Density) scoring 0 even when 4+
              // duties are visible.
              responsibilities={
                ((job.enrichedJd as { responsibilities?: string[] } | undefined)?.responsibilities
                  ?? (job.responsibilities as string[] | undefined)
                  ?? []) as string[]
              }
              technicalSkills={
                // T-1168 (Bug 5 canonical-fix, anti-padrão #6): prefira a fonte
                // ENRIQUECIDA quando o JD foi gerado/regenerado pela LIA. O
                // backend atualiza `enriched_jd.technical_skills` (lista normalizada
                // de N strings) mas a UI antes só lia `job.technicalRequirements`,
                // que pode estar desatualizado (somente os 5 originais do form).
                // Mesmo padrão da fix D2/D9: produtor decide a verdade visível.
                ((((job.enrichedJd as { technical_skills?: unknown[] } | undefined)?.technical_skills
                  ?? (job.technicalRequirements as unknown[] | undefined)
                  ?? []) as unknown[])
                  .map((r) => normalizeTechnicalRequirement(r))
                  .filter((s): s is string => Boolean(s)))
              }
              behavioralCompetencies={
                // T-1168 — idem: `enriched_jd.behavioral_competencies` tem a lista
                // canônica pós-enriquecimento; fallback ao snapshot do form.
                ((((job.enrichedJd as { behavioral_competencies?: unknown[] } | undefined)?.behavioral_competencies
                  ?? (job.behavioralCompetencies as unknown[] | undefined)
                  ?? []) as unknown[])
                  .map((c) => {
                    if (typeof c === 'string') return c
                    const rec = c as Record<string, unknown>
                    return (rec.competency || rec.name || rec.text || '') as string
                  })
                  .filter((s): s is string => Boolean(s)))
              }
              // Audit task #531 (G23-01) — leitura unificada via helper canônico
              // `getJobSeniority` (precedência `seniority` → `level` legacy);
              // substitui o fallback inline da rev. 20 sem mudar comportamento.
              seniority={getJobSeniority(job as { seniority?: string | null; level?: string | null })}
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
                if (!jobId || jobId === 'undefined') { console.error('[onSaveEnrichedJD] jobId inválido', job); throw new Error('ID da vaga inválido. Recarregue a página.') }
                await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enriched_jd: enrichedData }) })
                onJobUpdate?.({ ...job, enrichedJd: enrichedData })
              }}
              onUpdateOfficialJD={async (updates) => {
                if (!job) return
                const jobId = job.backendId || job.jobId || String(job.id)
                if (!jobId || jobId === 'undefined') { console.error('[onUpdateOfficialJD] jobId inválido', job); throw new Error('ID da vaga inválido. Recarregue a página.') }
                // T-1166 — JDArrayEditor edits `responsibilities` as the
                // duties list. We MUST send it to the dedicated backend column
                // (migration 132) instead of overloading `requirements`.
                await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ description: updates.description, responsibilities: updates.responsibilities, requirements: updates.requirements, technical_requirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })), behavioral_competencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) }) })
                onJobUpdate?.({ ...job, description: updates.description || job.description, responsibilities: updates.responsibilities || job.responsibilities, requirements: updates.requirements || job.requirements, technicalRequirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })) || job.technicalRequirements, behavioralCompetencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) || job.behavioralCompetencies })
              }}
              onSaveDefinitiva={async (enrichedData, updates) => {
                if (!job) return
                const jobId = job.backendId || job.jobId || String(job.id)
                if (!jobId || jobId === 'undefined') { console.error('[onSaveDefinitiva] jobId inválido', job); throw new Error('ID da vaga inválido. Recarregue a página.') }
                // P1-1 fix: 1 PUT atômico com enriched_jd + campos canônicos
                await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enriched_jd: enrichedData, description: updates.description, responsibilities: updates.responsibilities, requirements: updates.requirements, technical_requirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })), behavioral_competencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) }) })
                onJobUpdate?.({ ...job, enrichedJd: enrichedData, description: updates.description || job.description, responsibilities: updates.responsibilities || job.responsibilities, requirements: updates.requirements || job.requirements, technicalRequirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })) || job.technicalRequirements, behavioralCompetencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) || job.behavioralCompetencies })
              }}
              onSaveJDInline={async (updates) => {
                if (!job) return
                const jobId = job.backendId || job.jobId || String(job.id)
                if (!jobId || jobId === 'undefined') { console.error('[onSaveJDInline] jobId inválido', job); throw new Error('ID da vaga inválido. Recarregue a página.') }
                // T-1166 — same as onUpdateOfficialJD: persist responsibilities separately.
                await fetch(`/api/backend-proxy/job-vacancies/${jobId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ description: updates.description, responsibilities: updates.responsibilities, requirements: updates.requirements, technical_requirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })), behavioral_competencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) }) })
                onJobUpdate?.({ ...job, description: updates.description || job.description, responsibilities: updates.responsibilities || job.responsibilities, requirements: updates.requirements || job.requirements, technicalRequirements: updates.technicalSkills?.map((s: string) => ({ category: 'Técnica', technology: s, level: 'Intermediário', required: true })) || job.technicalRequirements, behavioralCompetencies: updates.behavioralCompetencies?.map((c: string) => ({ competency: c, weight: 'Importante' })) || job.behavioralCompetencies })
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
                          <span className={`text-micro font-semibold rounded-full w-5 h-5 flex items-center justify-center shrink-0 ${isAutomatic ? 'bg-lia-bg-tertiary' : 'text-lia-text-tertiary'}`}>{block.id}</span>
                          <span className={`text-xs font-medium ${isAutomatic ? 'text-lia-text-tertiary' : 'text-lia-text-primary'}`}>{block.name}</span>
                          {isAutomatic ? (
                            <span className="text-micro px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary rounded-full font-medium uppercase tracking-wide">Automático</span>
                          ) : totalBlockCount > 0 ? (
                            <span className="text-micro text-lia-text-tertiary">({totalBlockCount} {totalBlockCount === 1 ? 'pergunta' : 'perguntas'})</span>
                          ) : (
                            <span className="text-micro text-lia-text-muted italic">Nenhuma pergunta</span>
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
                            <p className="text-micro text-lia-text-muted mt-1 italic">{WSI_AUTOMATIC_MESSAGES[block.id].note}</p>
                          </div>
                        )}
                        {isAutomatic && !WSI_AUTOMATIC_MESSAGES[block.id] && (
                          <p className="text-micro text-lia-text-muted ml-7 mt-0.5">{block.description}</p>
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
