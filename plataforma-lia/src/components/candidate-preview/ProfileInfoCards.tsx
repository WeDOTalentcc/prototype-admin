"use client"

import { textStyles, badgeStyles } from '@/lib/design-tokens'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  GraduationCap, Award, Languages, DollarSign,
  User, Home, MapPin
} from "lucide-react"
import type { LanguageEntry } from './ProfileTabTypes'

interface ProfileInfoCardsProps {
  candidate: Record<string, unknown>
  formatCurrency: (value: number | string | null | undefined, currency?: string) => string
  languagesData: LanguageEntry[]
  hasSalaryData: () => boolean
  hasAddressData: () => boolean
  getAddressString: () => string
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
            <div key={`edu-${index}-${String(edu.institution || edu.school || index)}`} className={`flex items-start justify-between gap-2 ${index < (candidate.education as Record<string, unknown>[]).length - 1 ? 'pb-2 border-b border-lia-border-subtle' : ''}`}>
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

function ProfileCertificationsCard({ candidate }: { candidate: Record<string, unknown> }) {
  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center gap-1.5">
          <Award className="w-3.5 h-3.5 text-lia-text-primary" />
          <CardTitle className="text-xs font-semibold text-lia-text-primary">
            Cursos e Certificações
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-2.5 space-y-2">
        {candidate.certifications && (candidate.certifications as Record<string, unknown>[]).length > 0 ? (
          (candidate.certifications as (string | Record<string, unknown>)[]).map((cert: string | Record<string, unknown>, index: number) => {
            const certName = typeof cert === 'string' ? cert : ((cert.name || cert.title || 'Certificação') as string)
            const certIssuer = typeof cert === 'object' ? ((cert.issuer || cert.organization || '') as string) : ''
            const certDate = typeof cert === 'object' ? ((cert.date || cert.year || '') as string) : ''
            return (
              <div key={`cert-${index}-${certName || certIssuer}`} className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <h5 className={`${textStyles.label} truncate`}>
                    {certName}
                  </h5>
                  {certIssuer && <p className={textStyles.bodySmall}>{certIssuer}</p>}
                </div>
                {certDate && <span className="text-xs text-lia-text-primary flex-shrink-0">{certDate}</span>}
              </div>
            )
          })
        ) : (
          <p className={`${textStyles.description} italic`}>Não informado</p>
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
                <Badge className="text-xs px-1.5 py-0 h-4 bg-lia-interactive-active text-lia-text-primary border-lia-border-default font-semibold">
                  {lang.proficiency}
                </Badge>
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

function ProfilePreferencesCard({ candidate }: { candidate: Record<string, unknown> }) {
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
            <Badge className={badgeStyles.default}>
              {candidate.gender as string}
            </Badge>
          </div>
        )}
        {!!(candidate.work_model_preference || candidate.workModelPreference || candidate.workModel) && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Modelo de Trabalho</span>
            <Badge className={badgeStyles.default}>
              {(candidate.work_model_preference || candidate.workModelPreference || candidate.workModel) as string}
            </Badge>
          </div>
        )}
        {!!(candidate.contract_type_preference || candidate.contractTypePreference || candidate.contractType) && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Tipo de Contrato</span>
            <Badge className={badgeStyles.default}>
              {(candidate.contract_type_preference || candidate.contractTypePreference || candidate.contractType) as string}
            </Badge>
          </div>
        )}
        {candidate.is_remote !== undefined && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Aceita Remoto</span>
            <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.is_remote ? 'bg-status-success/15 text-status-success' : 'bg-lia-bg-tertiary text-lia-text-primary'}`}>
              {candidate.is_remote ? 'Sim' : 'Não'}
            </Badge>
          </div>
        )}
        {(candidate.willing_to_relocate !== undefined || candidate.willingToRelocate !== undefined) && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Aceita Mudança</span>
            <Badge className={`text-xs px-1.5 py-0 h-4 ${(candidate.willing_to_relocate ?? candidate.willingToRelocate) ? 'bg-status-success/15 text-status-success' : 'bg-lia-bg-tertiary text-lia-text-primary'}`}>
              {(candidate.willing_to_relocate ?? candidate.willingToRelocate) === true ? 'Sim' : 
               (candidate.willing_to_relocate ?? candidate.willingToRelocate) === false ? 'Não' : 
               String(candidate.willing_to_relocate ?? candidate.willingToRelocate)}
            </Badge>
          </div>
        )}
        {candidate.mobility !== undefined && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Disponibilidade Viagens</span>
            <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.mobility ? 'bg-status-success/15 text-status-success' : 'bg-lia-bg-tertiary text-lia-text-primary'}`}>
              {candidate.mobility === true ? 'Sim' : candidate.mobility === false ? 'Não' : String(candidate.mobility)}
            </Badge>
          </div>
        )}
        {candidate.communication_consent !== undefined && (
          <div className="flex items-center justify-between">
            <span className={textStyles.bodySmall}>Consentimento LGPD</span>
            <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.communication_consent ? 'bg-status-success/15 text-status-success' : 'bg-status-error/15 text-status-error'}`}>
              {candidate.communication_consent ? '✓ Consentido' : '✗ Não consentido'}
            </Badge>
          </div>
        )}
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
}: ProfileInfoCardsProps) {
  return (
    <>
      <ProfileEducationCard candidate={candidate} />
      <ProfileCertificationsCard candidate={candidate} />
      <ProfileLanguagesCard languagesData={languagesData} />
      <ProfileSalaryCard candidate={candidate} formatCurrency={formatCurrency} hasSalaryData={hasSalaryData} />
      <ProfilePreferencesCard candidate={candidate} />
      <ProfileAddressCard hasAddressData={hasAddressData} getAddressString={getAddressString} />
    </>
  )
}
