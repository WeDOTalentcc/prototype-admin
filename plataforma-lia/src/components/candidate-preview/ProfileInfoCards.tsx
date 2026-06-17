"use client"

import { useState } from "react"
import { textStyles, previewChipClasses, previewChipVariants } from '@/lib/design-tokens'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import {
  GraduationCap, Award, Languages, DollarSign,
  User, Home, MapPin, FileText, Pencil, Trash2
} from"lucide-react"
import type { LanguageEntry } from './ProfileTabTypes'
import { useCandidateEdit } from "@/components/candidate-profile/CandidateEditContext"
import { EditableField } from "@/components/candidate-profile/EditableField"
import { EditArrayItemModal } from "@/components/candidate-profile/EditArrayItemModal"
import { useCandidateArrayUpdate } from "@/hooks/candidates/use-candidate-array-update"

interface ProfileInfoCardsProps {
  candidate: Record<string, unknown>
  formatCurrency: (value: number | string | null | undefined, currency?: string) => string
  languagesData: LanguageEntry[]
  hasSalaryData: () => boolean
  hasAddressData: () => boolean
  getAddressString: () => string
  /** Navigate to Consentimento tab */
  onShowConsentHistory?: () => void
}

function ProfileNarrativeCard({ candidate }: { candidate: Record<string, unknown> }) {
  const { editable, updateField, isSaving } = useCandidateEdit()
  const selfIntro = (candidate.self_introduction as string | undefined) ?? ""
  if (!editable && !selfIntro) return null
  return (
    <Card className="border-lia-border-subtle col-span-2" data-testid="profile-narrative-card">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-lia-text-primary" />
          <CardTitle className="text-xs font-semibold text-lia-text-primary">
            Resumo Profissional
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-2.5">
        {editable && updateField ? (
          <EditableField
            value={selfIntro}
            onSave={async (value) => await updateField("self_introduction", value)}
            label="resumo profissional"
            placeholder="Resumo profissional do candidato"
            saving={isSaving?.("self_introduction") ?? false}
            emptyDisplay="Adicionar resumo profissional"
            type="textarea"
            showPencilWhenEmpty
            className="text-xs text-lia-text-primary leading-relaxed"
          />
        ) : (
          <p className="text-xs text-lia-text-primary leading-relaxed whitespace-pre-line">
            {selfIntro || "—"}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

function ProfileEducationCard({ candidate }: { candidate: Record<string, unknown> }) {
  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center gap-1.5">
          <GraduationCap className="w-3.5 h-3.5 text-lia-text-primary" />
          <CardTitle className="text-xs font-semibold text-lia-text-primary">
            Formação Acadêmica
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-2.5 space-y-2">
        {candidate.education && (candidate.education as Record<string, unknown>[]).length > 0 ? (
          (candidate.education as Record<string, unknown>[]).map((edu: Record<string, unknown>, index: number) => (
            <div key={`edu-${index}-${String(edu.institution || edu.school || index)}`} className={`flex items-start justify-between gap-2 ${index < (candidate.education as Record<string, unknown>[]).length - 1 ? 'pb-2' : ''}`}>
              <div className="min-w-0 flex-1">
                <h5 className={textStyles.label}>
                  {(edu.degree || edu.title || 'Formação') as string}{(edu.field_of_study || edu.fieldOfStudy) ? ` em ${(edu.field_of_study || edu.fieldOfStudy) as string}` : ''}
                </h5>
                <p className={textStyles.bodySmall}>
                  {(edu.school || edu.institution || 'Instituição não informada') as string}
                </p>
              </div>
              <span className="text-xs text-lia-text-primary flex-shrink-0">
                {(edu.start_date || edu.startDate || '') as string}{((edu.start_date || edu.startDate) && (edu.end_date || edu.endDate)) ? ' - ' : ''}{(edu.end_date || edu.endDate || '') as string}
              </span>
            </div>
          ))
        ) : (
          <p className={`${textStyles.description} italic`}>Não informado</p>
        )}
      </CardContent>
    </Card>
  )
}

type CertEntry = string | { name?: string; title?: string; issuer?: string; organization?: string; date?: string; year?: string }

function normalizeCertToString(cert: CertEntry): string {
  if (typeof cert === "string") return cert
  return (cert.name || cert.title || "").toString().trim()
}

function ProfileCertificationsCard({ candidate }: { candidate: Record<string, unknown> }) {
  const { editable, candidateId } = useCandidateEdit()
  const rawCerts = (candidate.certifications as CertEntry[] | undefined) ?? []
  const certStrings = rawCerts.map(normalizeCertToString).filter((s) => !!s)
  const { addItem, updateItem, removeItem, saving } = useCandidateArrayUpdate<string>(
    candidateId,
    "certifications",
    certStrings,
  )
  const [editIdx, setEditIdx] = useState<number | null>(null)
  const [adding, setAdding] = useState(false)

  const fields = [
    { name: "name", label: "Certificação", type: "text" as const, required: true, placeholder: "Ex: AWS Certified Solutions Architect – Associate" },
  ]

  return (
    <Card className="border-lia-border-subtle" data-testid="profile-certifications-card">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center justify-between gap-1.5">
          <div className="flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-lia-text-primary" />
            <CardTitle className="text-xs font-semibold text-lia-text-primary">
              Cursos e Certificações
            </CardTitle>
          </div>
          {editable && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => setAdding(true)}
              disabled={saving}
              aria-label="Adicionar certificação"
              data-testid="cert-add-btn"
            >
              <Pencil className="w-3 h-3" aria-hidden="true" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-2.5 space-y-2">
        {rawCerts.length > 0 ? (
          rawCerts.map((cert, index) => {
            const certName = normalizeCertToString(cert) || "Certificação"
            const certIssuer = typeof cert === 'object' ? ((cert.issuer || cert.organization || '') as string) : ''
            const certDate = typeof cert === 'object' ? ((cert.date || cert.year || '') as string) : ''
            return (
              <div key={`cert-${index}-${certName || certIssuer}`} className="flex items-start justify-between gap-2 group">
                <div className="min-w-0 flex-1">
                  <h5 className={`${textStyles.label} truncate`}>
                    {certName}
                  </h5>
                  {certIssuer && <p className={textStyles.bodySmall}>{certIssuer}</p>}
                </div>
                {certDate && <span className="text-xs text-lia-text-primary flex-shrink-0">{certDate}</span>}
                {editable && (
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-0.5 shrink-0">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-5 w-5 p-0"
                      onClick={() => setEditIdx(index)}
                      disabled={saving}
                      aria-label="Editar certificação"
                      data-testid={`cert-edit-btn-${index}`}
                    >
                      <Pencil className="w-2.5 h-2.5" aria-hidden="true" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-5 w-5 p-0 hover:text-status-error"
                      onClick={async () => { await removeItem(index) }}
                      disabled={saving}
                      aria-label="Remover certificação"
                      data-testid={`cert-remove-btn-${index}`}
                    >
                      <Trash2 className="w-2.5 h-2.5" aria-hidden="true" />
                    </Button>
                  </div>
                )}
              </div>
            )
          })
        ) : (
          <p className={`${textStyles.description} italic`}>Não informado</p>
        )}
        {editable && adding && (
          <EditArrayItemModal<{ name: string }>
            open={adding}
            onClose={() => setAdding(false)}
            onSave={async (values) => {
              const result = await addItem(values.name)
              if (result.success) setAdding(false)
              return result
            }}
            title="Adicionar Certificação"
            fields={fields}
            initialItem={null}
          />
        )}
        {editable && editIdx !== null && (
          <EditArrayItemModal<{ name: string }>
            open={editIdx !== null}
            onClose={() => setEditIdx(null)}
            onSave={async (values) => {
              const result = await updateItem(editIdx, values.name)
              if (result.success) setEditIdx(null)
              return result
            }}
            title="Editar Certificação"
            fields={fields}
            initialItem={{ name: certStrings[editIdx] || "" }}
          />
        )}
      </CardContent>
    </Card>
  )
}

function ProfileLanguagesCard({ languagesData }: { languagesData: LanguageEntry[] }) {
  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center gap-1.5">
          <Languages className="w-3.5 h-3.5 text-lia-text-primary" />
          <CardTitle className="text-xs font-semibold text-lia-text-primary">
            Idiomas
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-2.5 space-y-1.5">
        {languagesData.length > 0 ? (
          languagesData.map((lang, index) => (
            <div key={`lang-${lang.language || index}`} className="flex items-center justify-between">
              <span className={`${textStyles.bodySmall} font-medium`}>
                {lang.language}
              </span>
              {lang.proficiency && (
                <Chip variant="neutral" muted className={cn(previewChipClasses, 'bg-lia-interactive-active text-lia-text-primary border-lia-border-default')}>
                  {lang.proficiency}
                </Chip>
              )}
            </div>
          ))
        ) : (
          <p className={`${textStyles.description} italic`}>Não informado</p>
        )}
      </CardContent>
    </Card>
  )
}

function ProfileSalaryCard({ candidate, formatCurrency, hasSalaryData }: { candidate: Record<string, unknown>, formatCurrency: (value: number | string | null | undefined, currency?: string) => string, hasSalaryData: () => boolean }) {
  return (
    <Card className="border-lia-border-subtle col-span-2">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center gap-1.5">
          <DollarSign className="w-3.5 h-3.5 text-lia-text-primary" />
          <CardTitle className="text-xs font-semibold text-lia-text-primary">
            Remuneração
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-2.5">
        {hasSalaryData() ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className={textStyles.bodySmall}>Salário Atual</span>
              <span className={textStyles.label}>
                {formatCurrency((candidate.current_salary || candidate.currentSalary) as number | string | null, (candidate.salary_currency || candidate.salaryCurrency || 'BRL') as string)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className={textStyles.bodySmall}>Pretensão Salarial</span>
              <span className={textStyles.label}>
                {((candidate.desired_salary_min || candidate.desiredSalaryMin) && (candidate.desired_salary_max || candidate.desiredSalaryMax))
                  ? `${formatCurrency((candidate.desired_salary_min || candidate.desiredSalaryMin) as number | string | null)} - ${formatCurrency((candidate.desired_salary_max || candidate.desiredSalaryMax) as number | string | null)}`
                  : formatCurrency((candidate.desired_salary_min || candidate.desiredSalaryMin || candidate.desired_salary_max || candidate.desiredSalaryMax) as number | string | null)
                }
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className={textStyles.bodySmall}>Expectativa CLT</span>
              <span className={textStyles.label}>
                {formatCurrency((candidate.salary_expectation_clt || candidate.salaryExpectationClt) as number | string | null)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className={textStyles.bodySmall}>Expectativa PJ</span>
              <span className={textStyles.label}>
                {formatCurrency((candidate.salary_expectation_pj || candidate.salaryExpectationPj) as number | string | null)}
              </span>
            </div>
            {!!(candidate.salary_expectation_freelance || candidate.salaryExpectationFreelance) && (
              <div className="flex items-center justify-between">
                <span className={textStyles.bodySmall}>Expectativa Freelance</span>
                <span className={textStyles.label}>
                  {formatCurrency((candidate.salary_expectation_freelance || candidate.salaryExpectationFreelance) as number | string | null)}
                </span>
              </div>
            )}
          </div>
        ) : (
          <p className={`${textStyles.description} italic`}>Não informado</p>
        )}
      </CardContent>
    </Card>
  )
}

function ProfilePreferencesCard({ candidate, onShowConsentHistory }: { candidate: Record<string, unknown>; onShowConsentHistory?: () => void }) {
  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center gap-1.5">
          <User className="w-3.5 h-3.5 text-lia-text-primary" />
          <CardTitle className="text-xs font-semibold text-lia-text-primary">
            Preferências e Dados Pessoais
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-2.5 space-y-2">
        {!!candidate.gender && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Gênero</span>
            <Chip variant="neutral" muted className={previewChipVariants.neutral}>
              {candidate.gender as string}
            </Chip>
          </div>
        )}
        {!!(candidate.work_model_preference || candidate.workModelPreference || candidate.workModel) && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Modelo de Trabalho</span>
            <Chip variant="neutral" muted className={previewChipVariants.neutral}>
              {(candidate.work_model_preference || candidate.workModelPreference || candidate.workModel) as string}
            </Chip>
          </div>
        )}
        {!!(candidate.contract_type_preference || candidate.contractTypePreference || candidate.contractType) && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Tipo de Contrato</span>
            <Chip variant="neutral" muted className={previewChipVariants.neutral}>
              {(candidate.contract_type_preference || candidate.contractTypePreference || candidate.contractType) as string}
            </Chip>
          </div>
        )}
        {candidate.is_remote !== undefined && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Aceita Remoto</span>
            <Chip variant="neutral" muted className={previewChipVariants.neutral}>
              {candidate.is_remote ? 'Sim' : 'Não'}
            </Chip>
          </div>
        )}
        {(candidate.willing_to_relocate !== undefined || candidate.willingToRelocate !== undefined) && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Aceita Mudança</span>
            <Chip variant="neutral" muted className={previewChipVariants.neutral}>
              {(candidate.willing_to_relocate ?? candidate.willingToRelocate) === true ? 'Sim' :
               (candidate.willing_to_relocate ?? candidate.willingToRelocate) === false ? 'Não' :
               String(candidate.willing_to_relocate ?? candidate.willingToRelocate)}
            </Chip>
          </div>
        )}
        {candidate.mobility !== undefined && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Disponibilidade Viagens</span>
            <Chip variant="neutral" muted className={previewChipVariants.neutral}>
              {candidate.mobility === true ? 'Sim' : candidate.mobility === false ? 'Não' : String(candidate.mobility)}
            </Chip>
          </div>
        )}
        {candidate.communication_consent !== undefined && (
          <div className="flex items-start justify-between gap-2">
            <div>
              <span className={textStyles.bodySmall}>Consent. comunicação</span>
              {onShowConsentHistory && (
                <button
                  onClick={onShowConsentHistory}
                  className="block text-micro text-lia-text-muted hover:underline mt-0.5"
                >
                  → Ver histórico
                </button>
              )}
            </div>
            <Chip variant="neutral" muted className={previewChipVariants.neutral}>
              {candidate.communication_consent ? '✓ Consentido' : '✗ Não consentido'}
            </Chip>
          </div>
        )}
        <div className="flex items-start justify-between gap-2">
          <div>
            <span className={textStyles.bodySmall}>Consent. áudio triagem</span>
            {onShowConsentHistory && (
              <button
                onClick={onShowConsentHistory}
                className="block text-micro text-lia-text-muted hover:underline mt-0.5"
              >
                → Ver histórico
              </button>
            )}
          </div>
          <Chip variant="neutral" muted className={previewChipVariants.neutral}>
            —
          </Chip>
        </div>
      </CardContent>
    </Card>
  )
}

function ProfileAddressCard({ hasAddressData, getAddressString }: { hasAddressData: () => boolean, getAddressString: () => string }) {
  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center gap-1.5">
          <Home className="w-3.5 h-3.5 text-lia-text-primary" />
          <CardTitle className="text-xs font-semibold text-lia-text-primary">
            Endereço
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-2.5">
        {hasAddressData() ? (
          <div className="space-y-1">
            <div className="flex items-start gap-2">
              <MapPin className="w-3 h-3 text-lia-text-secondary mt-0.5 flex-shrink-0" />
              <div className="text-xs text-lia-text-primary whitespace-pre-line">
                {getAddressString()}
              </div>
            </div>
          </div>
        ) : (
          <p className={`${textStyles.description} italic`}>Não informado</p>
        )}
      </CardContent>
    </Card>
  )
}

export function ProfileInfoCards({
  candidate,
  formatCurrency,
  languagesData,
  hasSalaryData,
  hasAddressData,
  getAddressString,
  onShowConsentHistory,
}: ProfileInfoCardsProps) {
  return (
    <>
      <ProfileNarrativeCard candidate={candidate} />
      <ProfileEducationCard candidate={candidate} />
      <ProfileCertificationsCard candidate={candidate} />
      <ProfileLanguagesCard languagesData={languagesData} />
      <ProfileSalaryCard candidate={candidate} formatCurrency={formatCurrency} hasSalaryData={hasSalaryData} />
      <ProfilePreferencesCard candidate={candidate} onShowConsentHistory={onShowConsentHistory} />
      <ProfileAddressCard hasAddressData={hasAddressData} getAddressString={getAddressString} />
    </>
  )
}
