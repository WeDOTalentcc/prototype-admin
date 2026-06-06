"use client"

import React from "react"
import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { SCREENING_STATUS_LABELS, type ScreeningStatus } from "@/types/screening"
import { Card, CardContent } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import {
  Linkedin, Globe, Search, Plus, X, Copy, ExternalLink, Link, Languages
} from "lucide-react"
import { toast } from "sonner"
import { textStyles } from "@/lib/design-tokens"
import {
  LANGUAGE_OPTIONS,
  LEVEL_OPTIONS,
  inputClass,
  selectClass,
  labelClass,
  groupHeaderClass,
  formatDateValue,
} from "./job-edit-tab.constants"
import { ScreeningBadge } from "./ScreeningBadge"
import { LiaEditor } from "@/components/ui/lia-editor"
import { sanitizeHtml } from "@/lib/sanitize"
import { RemoteCombobox, type RemoteComboboxOption } from "@/components/ui/remote-combobox"
import { AccessListEditor } from "./AccessListEditor"
import {
  useJobStatuses, useJobPriorities, useJobUrgencyLevels,
  useJobWorkplaceTypes, useJobEmploymentTypes, useJobSeniorities,
  useDepartmentsSearch, useCitiesSearch,
} from "@/hooks/jobs/use-job-metadata"

function asOption(value: unknown): RemoteComboboxOption | null {
  if (value && typeof value === "object") {
    const v = value as Record<string, unknown>
    if (v.id !== undefined && v.name !== undefined) {
      return { id: v.id as string | number, name: String(v.name) }
    }
    return null
  }
  if (value) return { id: String(value), name: String(value) }
  return null
}

interface JobInfoGeralSectionProps {
  jobEditForm: Record<string, unknown>
  job?: Record<string, unknown> | null
  companyDefaults?: Record<string, unknown>
  isEditing: boolean
  updateField: (key: string, value: unknown) => void
  setActiveSection: (section: string) => void
  setStatusChangeConfirm: (state: { newStatus: string; screeningImpact: string } | null) => void
  getScreeningImpact: (status: string) => string
  publicLink?: string
}

export function JobInfoGeralSection({
  jobEditForm,
  job,
  companyDefaults,
  isEditing,
  updateField,
  setActiveSection,
  setStatusChangeConfirm,
  getScreeningImpact,
  publicLink,
}: JobInfoGeralSectionProps) {
  const [departmentQuery, setDepartmentQuery] = React.useState("")
  const [cityQuery, setCityQuery] = React.useState("")

  const { options: statusOptions, isLoading: statusLoading } = useJobStatuses()
  const { options: priorityOptions, isLoading: priorityLoading } = useJobPriorities()
  const { options: urgencyOptions, isLoading: urgencyLoading } = useJobUrgencyLevels()
  const { options: workplaceOptions, isLoading: workplaceLoading } = useJobWorkplaceTypes()
  const { options: employmentOptions, isLoading: employmentLoading } = useJobEmploymentTypes()
  const { options: seniorityOptions, isLoading: seniorityLoading } = useJobSeniorities()
  const { options: departmentOptions, isLoading: departmentLoading } = useDepartmentsSearch(departmentQuery)
  const { options: cityOptions, isLoading: cityLoading } = useCitiesSearch(cityQuery)

  return (
    <div className="space-y-5">
      <div>
        <h3 className={groupHeaderClass}>Gestão</h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="grid grid-cols-4 gap-4">
              <div>
                <label className={labelClass}>Status</label>
                <RemoteCombobox
                  value={asOption(jobEditForm.status)}
                  onChange={(opt) => {
                    const newStatus = opt?.name
                    if (!newStatus) return
                    const impact = getScreeningImpact(newStatus)
                    if (impact !== "none") {
                      setStatusChangeConfirm({ newStatus, screeningImpact: impact })
                    } else {
                      updateField("status", newStatus)
                    }
                  }}
                  options={statusOptions}
                  isLoading={statusLoading}
                  placeholder="Status"
                  disabled={!isEditing}
                />
              </div>
              <div>
                <label className={labelClass}>Prioridade</label>
                <RemoteCombobox
                  value={asOption(jobEditForm.priority)}
                  onChange={(opt) => updateField("priority", opt)}
                  options={priorityOptions}
                  isLoading={priorityLoading}
                  placeholder="Prioridade"
                  disabled={!isEditing}
                />
              </div>
              <div>
                <label className={labelClass}>Nível de Urgência</label>
                <RemoteCombobox
                  value={asOption(jobEditForm.urgencyLevel)}
                  onChange={(opt) => updateField("urgencyLevel", opt)}
                  options={urgencyOptions}
                  isLoading={urgencyLoading}
                  placeholder="Urgência"
                  disabled={!isEditing}
                />
              </div>
              <div>
                <label className={labelClass}>Triagem</label>
                <div
                  className={`w-full px-3 py-2 text-xs rounded-md border cursor-pointer transition-colors hover:bg-lia-interactive-hover ${
                    (job?.screeningStatus || "not_configured") === "active"
                      ? "border-status-success/30 bg-status-success/10/50 text-status-success dark:border-status-success/30 dark:bg-status-success/20"
                      : (job?.screeningStatus || "not_configured") === "paused"
                      ? "border-status-warning/30 bg-status-warning/10/50 text-status-warning dark:border-status-warning/30 dark:bg-status-warning/20"
                      : (job?.screeningStatus || "not_configured") === "completed"
                      ? "border-wedo-cyan/30 bg-wedo-cyan/10/50 text-wedo-cyan-dark dark:border-wedo-cyan/30"
                      : "border-lia-border-subtle bg-lia-bg-secondary text-lia-text-secondary"
                  }`}
                  onClick={() => setActiveSection("configuracoes")}
                  title="Clique para ir às Configurações de Triagem"
                >
                  {(() => {
                    const s = (job?.screeningStatus || "not_configured") as ScreeningStatus
                    const icons: Record<ScreeningStatus, string> = {
                      active: "●", paused: "◉", completed: "✓", not_started: "○", not_configured: "○",
                    }
                    return `${icons[s]} ${SCREENING_STATUS_LABELS[s]}`
                  })()}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className={groupHeaderClass}>Identificação</h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className={labelClass}>Título da Vaga<ScreeningBadge /></label>
                <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.title as string) || ""} onChange={(e) => updateField("title", e.target.value)} disabled={!isEditing} placeholder="Ex: Analista de Sistemas Sênior" />
              </div>
              <div>
                <label className={labelClass}>Departamento<ScreeningBadge /></label>
                <RemoteCombobox
                  value={asOption(jobEditForm.department)}
                  onChange={(opt) => updateField("department", opt)}
                  options={departmentOptions}
                  isLoading={departmentLoading}
                  onSearchChange={setDepartmentQuery}
                  placeholder="Selecione um departamento"
                  disabled={!isEditing}
                />
              </div>
              {jobEditForm.workModel !== "remoto" && (
                <div>
                  <label className={labelClass}>Endereço<ScreeningBadge /></label>
                  <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.location as string) || ""} onChange={(e) => updateField("location", e.target.value)} disabled={!isEditing} placeholder="Ex: Av. Paulista, 1000 - Bela Vista, São Paulo" />
                </div>
              )}
              <div>
                <label className={labelClass}>Cidade<ScreeningBadge /></label>
                <RemoteCombobox
                  value={asOption(jobEditForm.city)}
                  onChange={(opt) => updateField("city", opt)}
                  options={cityOptions}
                  isLoading={cityLoading}
                  onSearchChange={setCityQuery}
                  placeholder="Busque uma cidade"
                  disabled={!isEditing}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className={groupHeaderClass}>Classificação</h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>
                  Modelo de Trabalho<ScreeningBadge />
                  {Boolean((companyDefaults as Record<string, unknown>)?.workModel) && !jobEditForm.workModel && (
                    <span className="ml-1.5 text-micro text-wedo-cyan-dark font-normal">(padrão: {(companyDefaults as Record<string, unknown>)?.workModel as string})</span>
                  )}
                </label>
                <RemoteCombobox
                  value={asOption(jobEditForm.workModel)}
                  onChange={(opt) => updateField("workModel", opt?.name ?? null)}
                  options={workplaceOptions}
                  isLoading={workplaceLoading}
                  placeholder={
                    (companyDefaults as Record<string, unknown>)?.workModel
                      ? `Usar padrão (${(companyDefaults as Record<string, unknown>)?.workModel})`
                      : "Selecione o modelo de trabalho"
                  }
                  disabled={!isEditing}
                />
              </div>
              <div>
                <label className={labelClass}>
                  Tipo de Contrato<ScreeningBadge />
                  {Boolean((companyDefaults as Record<string, unknown>)?.employmentTypes) && ((companyDefaults as Record<string, unknown>)?.employmentTypes as string[]).length > 0 && !jobEditForm.type && (
                    <span className="ml-1.5 text-micro text-wedo-cyan-dark font-normal">(padrão: {((companyDefaults as Record<string, unknown>)?.employmentTypes as string[])[0]})</span>
                  )}
                </label>
                <RemoteCombobox
                  value={asOption(jobEditForm.type)}
                  onChange={(opt) => updateField("type", opt)}
                  options={employmentOptions}
                  isLoading={employmentLoading}
                  placeholder={
                    ((companyDefaults as Record<string, unknown>)?.employmentTypes as string[] | undefined)?.[0]
                      ? `Usar padrão (${((companyDefaults as Record<string, unknown>)?.employmentTypes as string[])[0]})`
                      : "Tipo de contrato"
                  }
                  disabled={!isEditing}
                />
              </div>
              <div>
                <label className={labelClass}>Nível<ScreeningBadge /></label>
                <RemoteCombobox
                  value={asOption(jobEditForm.level)}
                  onChange={(opt) => updateField("level", opt)}
                  options={seniorityOptions}
                  isLoading={seniorityLoading}
                  placeholder="Senioridade"
                  disabled={!isEditing}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className={groupHeaderClass}>Prazos & Timeline</h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Data de Abertura</label>
                <input type="date" className={inputClass(!isEditing)} value={formatDateValue(jobEditForm.openDate)} onChange={(e) => updateField("openDate", e.target.value)} disabled={!isEditing} />
              </div>
              <div>
                <label className={labelClass}>Prazo Final</label>
                <input type="date" className={inputClass(!isEditing)} value={formatDateValue(jobEditForm.deadline)} onChange={(e) => updateField("deadline", e.target.value)} disabled={!isEditing} />
              </div>
              <div>
                <label className={labelClass}>Prazo Triagem</label>
                <input type="date" className={inputClass(!isEditing)} value={formatDateValue(jobEditForm.deadlineScreening)} onChange={(e) => updateField("deadlineScreening", e.target.value)} disabled={!isEditing} />
              </div>
              <div>
                <label className={labelClass}>Prazo Shortlist</label>
                <input type="date" className={inputClass(!isEditing)} value={formatDateValue(jobEditForm.deadlineShortlist)} onChange={(e) => updateField("deadlineShortlist", e.target.value)} disabled={!isEditing} />
              </div>
              <div className="col-span-2">
                <label className={labelClass}>Prazo Fechamento</label>
                <input type="date" className={inputClass(!isEditing)} value={formatDateValue(jobEditForm.deadlineClosing)} onChange={(e) => updateField("deadlineClosing", e.target.value)} disabled={!isEditing} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className={groupHeaderClass}>Descrição da Vaga</h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            <div>
              <label className={labelClass}>Descrição da Vaga<ScreeningBadge /></label>
              {isEditing ? (
                <LiaEditor
                  content={(jobEditForm.description as string) || ""}
                  onUpdate={(html) => updateField("description", html)}
                  placeholder="Descrição detalhada da vaga..."
                  toolbar="basic"
                  minHeight="300px"
                  disabled={!isEditing}
                />
              ) : (
                <div
                  className={`${inputClass(!isEditing)} resize-vertical min-h-[300px] prose prose-sm max-w-none p-3`}
                  dangerouslySetInnerHTML={{ __html: sanitizeHtml((jobEditForm.description as string) || '') || '<span class="text-lia-text-disabled">Descrição detalhada da vaga...</span>' }}
                />
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className={groupHeaderClass}>
          Idiomas<ScreeningBadge />
          {Boolean((companyDefaults as Record<string, unknown>)?.defaultLanguages) && ((companyDefaults as Record<string, unknown>)?.defaultLanguages as string[]).length > 0 && (
            <span className="ml-1.5 text-micro text-wedo-cyan-dark font-normal normal-case tracking-normal">
              (padrão empresa: {((companyDefaults as Record<string, unknown>)?.defaultLanguages as string[]).join(", ")})
            </span>
          )}
        </h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            {(() => {
              const langs = (jobEditForm.languages || []) as Array<{ language: string; level: string; required?: boolean }>
              const addLanguage = () => updateField("languages", [...langs, { language: "", level: "intermediario", required: false }])
              const removeLanguage = (idx: number) => updateField("languages", langs.filter((_, i) => i !== idx))
              const updateLanguage = (idx: number, field: string, value: unknown) =>
                updateField("languages", langs.map((l, i) => (i === idx ? { ...l, [field]: value } : l)))
              return (
                <div className="space-y-3">
                  {langs.length === 0 && !isEditing && (
                    <p className="text-xs text-lia-text-tertiary italic">Nenhum idioma adicionado</p>
                  )}
                  {langs.map((lang, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-3 bg-lia-bg-secondary/50 rounded-xl">
                      <Languages className="w-4 h-4 text-lia-text-tertiary flex-shrink-0" />
                      <div className="flex-1 grid grid-cols-3 gap-3">
                        <div>
                          <label className="text-micro text-lia-text-secondary mb-1 block">Idioma</label>
                          <select className={selectClass(!isEditing)} value={lang.language || ""} onChange={(e) => updateLanguage(idx, "language", e.target.value)} disabled={!isEditing}>
                            <option value="">Selecione...</option>
                            {LANGUAGE_OPTIONS.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="text-micro text-lia-text-secondary mb-1 block">Nível</label>
                          <select className={selectClass(!isEditing)} value={lang.level || "intermediario"} onChange={(e) => updateLanguage(idx, "level", e.target.value)} disabled={!isEditing}>
                            {LEVEL_OPTIONS.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                          </select>
                        </div>
                        <div className="flex items-end gap-2">
                          <div className="flex-1">
                            <label className="text-micro text-lia-text-secondary mb-1 block">Obrigatório</label>
                            <div className="flex items-center gap-2 h-[38px]">
                              <Switch checked={!!lang.required} onCheckedChange={(val: boolean) => updateLanguage(idx, "required", val)} disabled={!isEditing} className="data-[state=checked]:bg-lia-btn-primary-bg dark:data-[state=checked]:bg-lia-interactive-active" />
                              <span className="text-xs text-lia-text-secondary">{lang.required ? "Sim" : "Não"}</span>
                            </div>
                          </div>
                          {isEditing && (
                            <button onClick={() => removeLanguage(idx)} className="p-1.5 mb-1 rounded-lg hover:bg-status-error/10 dark:hover:bg-status-error/10/30 text-lia-text-tertiary hover:text-status-error transition-colors">
                              <X className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  {isEditing && (
                    <Button onClick={addLanguage} variant="outline" size="sm" className="gap-1.5 text-xs rounded-md w-full border-dashed">
                      <Plus className="w-3.5 h-3.5" />Adicionar Idioma
                    </Button>
                  )}
                </div>
              )
            })()}
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className={groupHeaderClass}>Ações Afirmativas<ScreeningBadge /></h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <Switch checked={!!jobEditForm.isAffirmative} onCheckedChange={(val: boolean) => updateField("isAffirmative", val)} disabled={!isEditing} />
                  <label className={textStyles.label}>Vaga Afirmativa</label>
                </div>
                <div>
                  <label className={labelClass}>Critério Principal</label>
                  <select value={(jobEditForm.affirmativeCriteriaPrimary as string) || ""} onChange={(e) => updateField("affirmativeCriteriaPrimary", e.target.value)} disabled={!isEditing || !jobEditForm.isAffirmative} className={selectClass(!isEditing || !jobEditForm.isAffirmative)}>
                    <option value="">Selecione...</option>
                    <option value="gender">Gênero</option>
                    <option value="race_ethnicity">Raça/Etnia</option>
                    <option value="disability">PCD</option>
                    <option value="lgbtqia">LGBTQIA+</option>
                    <option value="age">50+</option>
                    <option value="refugee">Refugiado</option>
                    <option value="indigenous">Indígena</option>
                    <option value="other">Outro</option>
                  </select>
                </div>
              </div>
              {(jobEditForm.isAffirmative as boolean) && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className={labelClass}>Critério Secundário (opcional)</label>
                      <select value={(jobEditForm.affirmativeCriteriaSecondary as string) || ""} onChange={(e) => updateField("affirmativeCriteriaSecondary", e.target.value)} disabled={!isEditing} className={selectClass(!isEditing)}>
                        <option value="">Nenhum</option>
                        <option value="gender">Gênero</option>
                        <option value="race_ethnicity">Raça/Etnia</option>
                        <option value="disability">PCD</option>
                        <option value="lgbtqia">LGBTQIA+</option>
                        <option value="age">50+</option>
                        <option value="refugee">Refugiado</option>
                        <option value="indigenous">Indígena</option>
                        <option value="other">Outro</option>
                      </select>
                    </div>
                    <div>
                      <label className={labelClass}>Descrição</label>
                      <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.affirmativeDescription as string) || ""} onChange={(e) => updateField("affirmativeDescription", e.target.value)} disabled={!isEditing} placeholder="Ex: Mulheres negras, PCD motora" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center gap-3">
                      <Switch checked={!!jobEditForm.affirmativeDocumentRequired} onCheckedChange={(val: boolean) => updateField("affirmativeDocumentRequired", val)} disabled={!isEditing} />
                      <label className={textStyles.label}>Exige Documentação</label>
                    </div>
                    {(jobEditForm.affirmativeDocumentRequired as boolean) && (
                      <div>
                        <label className={labelClass}>Tipos de Documento</label>
                        <input type="text" className={inputClass(!isEditing)} value={((jobEditForm.affirmativeDocumentTypes as string[]) || []).join(", ")} onChange={(e) => updateField("affirmativeDocumentTypes", e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean))} disabled={!isEditing} placeholder="Ex: laudo_pcd, autodeclaracao_racial" />
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className={groupHeaderClass}>Canais de Publicação</h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="space-y-0">
              <div className="flex items-center justify-between py-2.5 dark:border-lia-border-strong">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-wedo-cyan/10 flex items-center justify-center"><Linkedin className="w-4 h-4 text-wedo-cyan-dark" /></div>
                  <div>
                    <span className="text-xs font-medium text-lia-text-primary">LinkedIn</span>
                    <p className="text-xs text-lia-text-secondary">Publicar vaga no LinkedIn</p>
                  </div>
                </div>
                <Switch checked={!!jobEditForm.publishedLinkedIn} onCheckedChange={(val: boolean) => updateField("publishedLinkedIn", val)} disabled={!isEditing} />
              </div>
              <div className="flex items-center justify-between py-2.5 dark:border-lia-border-strong">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-status-success/10 dark:bg-status-success/20 flex items-center justify-center"><Globe className="w-4 h-4 text-status-success" /></div>
                  <div>
                    <span className="text-xs font-medium text-lia-text-primary">Website</span>
                    <p className="text-xs text-lia-text-secondary">Publicar no site da empresa</p>
                  </div>
                </div>
                <Switch checked={!!jobEditForm.publishedWebsite} onCheckedChange={(val: boolean) => updateField("publishedWebsite", val)} disabled={!isEditing} />
              </div>
              <div className="flex items-center justify-between py-2.5">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-wedo-purple/10 dark:bg-wedo-purple/20 flex items-center justify-center"><Search className="w-4 h-4 text-wedo-purple" /></div>
                  <div>
                    <span className="text-xs font-medium text-lia-text-primary">Indeed</span>
                    <p className="text-xs text-lia-text-secondary">Publicar vaga no Indeed</p>
                  </div>
                </div>
                <Switch checked={!!jobEditForm.publishedIndeed} onCheckedChange={(val: boolean) => updateField("publishedIndeed", val)} disabled={!isEditing} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className={groupHeaderClass}>Visibilidade & Confidencialidade</h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="space-y-4">
              {/* Sprint 1 RBAC (2026-05-25): Single source of truth = visibility (canonical lowercase).
                  Removido Switch isConfidential legacy — visibility="confidential" é canonical.
                  Backend: app/api/v1/job_vacancies/crud.py:list_job_vacancies + get_job_vacancy
                  filtram por visibility === "confidential" + access_list/created_by/recruiter_email.
                  Plan canonical: ~/.claude/plans/jolly-roaming-moler.md */}
              <div>
                <label className={labelClass}>Visibilidade da vaga</label>
                <select
                  value={(jobEditForm.visibility as string) || "public"}
                  onChange={(e) => {
                    const v = e.target.value
                    updateField("visibility", v)
                    // Sync legacy is_confidential (backend bool) com visibility canonical
                    updateField("isConfidential", v === "confidential")
                  }}
                  disabled={!isEditing}
                  className={selectClass(!isEditing)}
                  data-testid="job-visibility-select"
                >
                  <option value="public">Pública — todos recrutadores da empresa veem</option>
                  <option value="internal">Interna — só equipe interna, não publica em job boards</option>
                  <option value="confidential">Confidencial — só owner + equipe de acesso + admin</option>
                </select>
                <p className="text-xs text-lia-text-tertiary mt-1.5">
                  Vagas confidenciais (C-level, M&A, substituições internas) ficam visíveis apenas para owner, equipe de acesso e admin do tenant.
                </p>
              </div>

              {/* Sprint 1 RBAC (2026-05-25): Hiring Team UI — acesso editável quando confidencial.
                  Backend persiste em access_list (ARRAY[String]). Quem entra aqui vê a vaga
                  no Kanban e pode interagir. created_by + recruiter_email sempre têm acesso (auto). */}
              {jobEditForm.visibility === "confidential" && (
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 space-y-3" data-testid="job-access-list-section">
                  <div className="flex items-start gap-2">
                    <div className="text-amber-600 mt-0.5">🔒</div>
                    <div className="flex-1">
                      <label className={labelClass}>Equipe com acesso à vaga confidencial</label>
                      <p className="text-xs text-lia-text-secondary mt-0.5">
                        Adicione emails de recrutadores ou hiring managers que precisam ver esta vaga. Owner ({(job?.recruiter_email as string) || "você"}) já tem acesso automático.
                      </p>
                    </div>
                  </div>

                  <AccessListEditor
                    accessList={(jobEditForm.accessList as string[]) || (jobEditForm.access_list as string[]) || []}
                    onChange={(newList) => {
                      updateField("accessList", newList)
                      updateField("access_list", newList)
                    }}
                    disabled={!isEditing}
                  />
                </div>
              )}

              <div>
                <label className={labelClass}>Nome da Empresa (mascarado)</label>
                <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.maskedCompanyName as string) || ""} onChange={(e) => updateField("maskedCompanyName", e.target.value)} disabled={!isEditing} placeholder="Ex: Empresa do segmento de tecnologia" />
                <p className="text-xs text-lia-text-tertiary mt-1.5">
                  Nome alternativo exibido em job boards públicos quando a vaga é confidencial.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className={groupHeaderClass}>Link de Candidatura</h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            {(jobEditForm.status === "Ativa" || jobEditForm.status === "Pausada" || jobEditForm.status === "Paralisada" || jobEditForm.status === "Concluída") && (publicLink || jobEditForm.public_url) ? (
              <div className="space-y-2">
                <p className="text-xs text-lia-text-secondary">Link público para candidatos se candidatarem:</p>
                <div className="flex items-center gap-2">
                  <input type="text" readOnly value={publicLink || (jobEditForm.public_url as string) || ""} className="flex-1 px-3 py-2 text-xs text-lia-text-primary bg-lia-bg-secondary border border-lia-border-subtle rounded-xl" onClick={(e) => (e.target as HTMLInputElement).select()} />
                  <button onClick={() => { navigator.clipboard.writeText(publicLink || (jobEditForm.public_url as string) || ""); toast.success("Link copiado!") }} className="p-2 rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active transition-colors flex-shrink-0" title="Copiar link">
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                  <a href={publicLink || (jobEditForm.public_url as string) || "#"} target="_blank" rel="noopener noreferrer" className="p-2 rounded-xl border border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors flex-shrink-0" title="Abrir link">
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
                <Link className="w-3.5 h-3.5" />
                <span>Publique a vaga para gerar o link de candidatura</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
